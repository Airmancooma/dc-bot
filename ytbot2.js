const Discord = require('discord.js');
const { Intents } = Discord;
const { joinVoiceChannel, createAudioPlayer, createAudioResource, AudioPlayerStatus } = require('@discordjs/voice');
const yts = require('yt-search');
const ytdl = require('ytdl-core');
const client = new Discord.Client({ intents: [Intents.FLAGS.GUILDS, Intents.FLAGS.GUILD_MESSAGES, Intents.FLAGS.GUILD_VOICE_STATES] });

let currentResource = null;
let currentPlayer = null;
let isPlaying = false;
const queue = [];

client.on('ready', () => {
  console.log(`Logged in as ${client.user.tag}!`);
});

client.on('messageCreate', async (message) => {
  if (message.author.bot || !message.content.startsWith('!')) return;

  const args = message.content.slice(1).trim().split(/ +/);
  const command = args.shift().toLowerCase();

  if (command === 'play') {
    if (!args.length) {
      message.channel.send('Kedves polgártárs, legyen szíves megosztani velünk egy YouTube-videó hivatkozást!');
      return;
    }

    const url = args[0];
    if (!ytdl.validateURL(url)) {
      message.channel.send('Kedves polgártárs, kérem, érvényes YouTube-videó hivatkozást osszon meg velünk!');
      return;
    }
    const videoInfo = await yts({ videoId: ytdl.getURLVideoID(url) });

    if (!videoInfo) {
      message.channel.send('Sajnálom, de az Ön által megadott videót nem sikerült megtalálnom.');
      return;
    }

    queue.push({ url, title: videoInfo.title });

    if (isPlaying) {
      message.channel.send(`Hozzáadtam a nemzeti várólistához: ${videoInfo.title}`);
      return;
    }

    const voiceChannel = message.member.voice.channel;

    if (!voiceChannel) {
      message.channel.send('Kedves polgártárs, kérem, csatlakozzon egy hangcsatornához a parancs használatához!');
      return;
    }

    const connection = joinVoiceChannel({
      channelId: voiceChannel.id,
      guildId: voiceChannel.guild.id,
      adapterCreator: voiceChannel.guild.voiceAdapterCreator,
    });

    const videoToPlay = queue.shift();
    currentResource = createAudioResource(ytdl(videoToPlay.url, { filter: 'audioonly', quality: 'highestaudio', highWaterMark: 1 << 25 }));
    currentPlayer = createAudioPlayer();

    currentPlayer.play(currentResource);

    connection.subscribe(currentPlayer);

    isPlaying = true;

    currentPlayer.on(AudioPlayerStatus.Idle, () => {
      if (queue.length > 0) {
        const nextVideo = queue.shift();
        currentResource = createAudioResource(ytdl(nextVideo.url, { filter: 'audioonly', quality: 'highestaudio', highWaterMark: 1 << 25 }));
        currentPlayer.play(currentResource);
        message.channel.send(`Tisztelt polgártársak, most előadásra kerül: ${nextVideo.title}`);
      } else {
        connection.destroy();
        currentResource = null;
        currentPlayer = null;
        isPlaying = false;
      }
    });

    await message.channel.send(`Tisztelt polgártársak, most előadásra kerül: ${videoInfo.title}`);
  }

  if (command === 'skip') {
    const voiceChannel = message.member.voice.channel;

    if (!voiceChannel) {
      message.channel.send(' Kedves polgártárs, kérem, csatlakozzon egy hangcsatornához a parancs használatához!');
      return;
    }
    if (!currentResource || !currentPlayer || !isPlaying) {
      message.channel.send('Jelen pillanatban nincs lejátszás alatt álló zene, amit átugorhatna.');
      return;
    }

    if (queue.length > 0) {
      const nextVideo = queue.shift();
      currentResource = createAudioResource(ytdl(nextVideo.url, { filter: 'audioonly', quality: 'highestaudio', highWaterMark: 1 << 25 }));
      currentPlayer.play(currentResource);
      message.channel.send(`Tisztelt polgártársak, most előadásra kerül: ${nextVideo.title}`);
    } else {
      currentPlayer.stop();
      message.channel.send('Nincs több zene a várólistán, a lejátszás befejeződött.');
      isPlaying = false;
    }
  }
  if (command === 'stop') {
    const voiceChannel = message.member.voice.channel;

    if (!voiceChannel) {
      message.channel.send('Kedves polgártárs, kérem, csatlakozzon egy hangcsatornához a parancs használatához!');
      return;
    }

    if (!currentResource || !currentPlayer || !isPlaying) {
      message.channel.send('Jelen pillanatban nincs lejátszás alatt álló zene, amit leállíthatna.');
      return;
    }

    currentPlayer.stop();
    currentResource = null;
    isPlaying = false;

    const connection = joinVoiceChannel({
      channelId: voiceChannel.id,
      guildId: voiceChannel.guild.id,
      adapterCreator: voiceChannel.guild.voiceAdapterCreator,
    });
    connection.destroy();

    message.channel.send('A zene leállítása és a hangcsatornáról való távozás megtörtént.');
  }
  if (command === 'help') { // új parancs hozzáadása
    message.reply('Tisztelt polgártársak, engedjék meg, hogy bemutassam magam és a szolgáltatásaimat!\n\n!play {url} - Lejátszom az Ön által megosztott tartalmat.\n!skip - Kérem ezt a parancsot használva ugorhatnak a következő videóra vagy zeneszámra.\n!stop - Tisztelt polgártársak, szeretném felhívni a figyelmüket, hogy ezen parancs segítségével bármikor meg tudom állítani az éppen zajló zenét, majd távozom a hangcsatornából.');
  }
});


client.on('error', (error) => {
  console.error('The bot encountered an error:', error);
});

client.login('MTA5OTcyNDEzMjY4NzU1NjY4OQ.GNz8LZ.sUGI2EjPAscASxWRHDrFquRjg1FtjVWQ-iGxt0');
